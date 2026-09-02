import { and, eq } from "drizzle-orm";
import { drizzle } from "drizzle-orm/mysql2";
import { InsertUser, priceAlerts, pushDevices, savedCollectionMembers, savedCollections, users } from "../drizzle/schema";
import { ENV } from "./_core/env";

let _db: ReturnType<typeof drizzle> | null = null;

// Lazily create the drizzle instance so local tooling can run without a DB.
export async function getDb() {
  if (!_db && process.env.DATABASE_URL) {
    try {
      _db = drizzle(process.env.DATABASE_URL);
    } catch {
      console.warn("[Database] Failed to connect");
      _db = null;
    }
  }
  return _db;
}

export async function upsertUser(user: InsertUser): Promise<void> {
  if (!user.openId) {
    throw new Error("User openId is required for upsert");
  }

  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot upsert user: database not available");
    return;
  }

  try {
    const values: InsertUser = {
      openId: user.openId,
    };
    const updateSet: Record<string, unknown> = {};

    const textFields = ["name", "email", "loginMethod"] as const;
    type TextField = (typeof textFields)[number];

    const assignNullable = (field: TextField) => {
      const value = user[field];
      if (value === undefined) return;
      const normalized = value ?? null;
      values[field] = normalized;
      updateSet[field] = normalized;
    };

    textFields.forEach(assignNullable);

    if (user.lastSignedIn !== undefined) {
      values.lastSignedIn = user.lastSignedIn;
      updateSet.lastSignedIn = user.lastSignedIn;
    }
    if (user.role !== undefined) {
      values.role = user.role;
      updateSet.role = user.role;
    } else if (user.openId === ENV.ownerOpenId) {
      values.role = "admin";
      updateSet.role = "admin";
    }

    if (!values.lastSignedIn) {
      values.lastSignedIn = new Date();
    }

    if (Object.keys(updateSet).length === 0) {
      updateSet.lastSignedIn = new Date();
    }

    await db.insert(users).values(values).onDuplicateKeyUpdate({
      set: updateSet,
    });
  } catch {
    console.error("[Database] Failed to upsert user");
    throw new Error("USER_STORAGE_FAILED");
  }
}

export async function getUserByOpenId(openId: string) {
  const db = await getDb();
  if (!db) {
    console.warn("[Database] Cannot get user: database not available");
    return undefined;
  }

  const result = await db.select().from(users).where(eq(users.openId, openId)).limit(1);

  return result.length > 0 ? result[0] : undefined;
}

export type SyncedAlertInput = { offerId: number; name: string; threshold: number; currency: string; createdAt: string };

export async function getUserPriceAlerts(userId: number) {
  const db = await getDb();
  if (!db) throw new Error("Alert storage unavailable");
  return db.select().from(priceAlerts).where(eq(priceAlerts.userId, userId));
}

export async function syncUserPriceAlerts(userId: number, alerts: SyncedAlertInput[]) {
  const db = await getDb();
  if (!db) throw new Error("Alert storage unavailable");
  for (const alert of alerts) {
    await db.insert(priceAlerts).values({ userId, offerId: alert.offerId, productName: alert.name, threshold: alert.threshold.toFixed(2), currency: alert.currency, clientCreatedAt: new Date(alert.createdAt) }).onDuplicateKeyUpdate({ set: { productName: alert.name, threshold: alert.threshold.toFixed(2), currency: alert.currency, status: "active", clientCreatedAt: new Date(alert.createdAt) } });
  }
  return getUserPriceAlerts(userId);
}

export async function registerPushDevice(userId: number, device: { expoToken: string; platform: "ios" | "android"; permission: "granted" | "denied" }) {
  const db = await getDb();
  if (!db) throw new Error("Alert storage unavailable");
  await db.insert(pushDevices).values({ userId, ...device }).onDuplicateKeyUpdate({ set: { userId, platform: device.platform, permission: device.permission } });
  return { registered: device.permission === "granted" };
}

export type SyncedCollectionInput = { clientId: string; name: string; createdAt: string; updatedAt: string; deletedAt: string | null; offerIds: number[] };
export type SyncedCollection = { clientId: string; name: string; createdAt: string; updatedAt: string; deletedAt: string | null; offerIds: number[] };

export async function getUserSavedCollections(userId: number): Promise<SyncedCollection[]> {
  const db = await getDb();
  if (!db) throw new Error("Collection storage unavailable");
  const collections = await db.select().from(savedCollections).where(eq(savedCollections.userId, userId));
  if (!collections.length) return [];
  const members = await Promise.all(collections.filter((collection) => !collection.deletedAt).map(async (collection) => ({ collectionId: collection.id, rows: await db.select().from(savedCollectionMembers).where(eq(savedCollectionMembers.collectionId, collection.id)) })));
  const byId = new Map(members.map((entry) => [entry.collectionId, entry.rows.map((row) => row.offerId)]));
  return collections.map((collection) => ({ clientId: collection.clientId, name: collection.name, createdAt: collection.clientCreatedAt.toISOString(), updatedAt: collection.clientUpdatedAt.toISOString(), deletedAt: collection.deletedAt?.toISOString() ?? null, offerIds: collection.deletedAt ? [] : byId.get(collection.id) ?? [] }));
}

export async function syncUserSavedCollections(userId: number, collections: SyncedCollectionInput[]): Promise<SyncedCollection[]> {
  const db = await getDb();
  if (!db) throw new Error("Collection storage unavailable");
  for (const collection of collections) {
    const stored = await db.select().from(savedCollections).where(and(eq(savedCollections.userId, userId), eq(savedCollections.clientId, collection.clientId))).limit(1);
    const existing = stored[0];
    const incomingUpdatedAt = new Date(collection.updatedAt);
    if (!existing) await db.insert(savedCollections).values({ userId, clientId: collection.clientId, name: collection.name, clientCreatedAt: new Date(collection.createdAt), clientUpdatedAt: incomingUpdatedAt, deletedAt: collection.deletedAt ? new Date(collection.deletedAt) : null });
    else {
      const existingVersion = Math.max(existing.clientUpdatedAt.getTime(), existing.deletedAt?.getTime() ?? 0);
      const incomingVersion = Math.max(incomingUpdatedAt.getTime(), collection.deletedAt ? new Date(collection.deletedAt).getTime() : 0);
      if (incomingVersion >= existingVersion) await db.update(savedCollections).set({ name: collection.name, clientCreatedAt: new Date(collection.createdAt), clientUpdatedAt: incomingUpdatedAt, deletedAt: collection.deletedAt ? new Date(collection.deletedAt) : null }).where(eq(savedCollections.id, existing.id));
    }
    const resolved = await db.select().from(savedCollections).where(and(eq(savedCollections.userId, userId), eq(savedCollections.clientId, collection.clientId))).limit(1);
    const collectionId = resolved[0]?.id;
    if (!collectionId) continue;
    const current = resolved[0];
    if (current && current.clientUpdatedAt.getTime() <= incomingUpdatedAt.getTime()) {
      await db.delete(savedCollectionMembers).where(eq(savedCollectionMembers.collectionId, collectionId));
      if (!current.deletedAt) for (const offerId of collection.offerIds) await db.insert(savedCollectionMembers).values({ collectionId, offerId });
    }
  }
  return getUserSavedCollections(userId);
}
