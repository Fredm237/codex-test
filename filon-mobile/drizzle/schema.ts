import { decimal, int, mysqlEnum, mysqlTable, text, timestamp, uniqueIndex, varchar } from "drizzle-orm/mysql-core";

/**
 * Core user table backing auth flow.
 * Extend this file with additional tables as your product grows.
 * Columns use camelCase to match both database fields and generated types.
 */
export const users = mysqlTable("users", {
  /**
   * Surrogate primary key. Auto-incremented numeric value managed by the database.
   * Use this for relations between tables.
   */
  id: int("id").autoincrement().primaryKey(),
  /** Manus OAuth identifier (openId) returned from the OAuth callback. Unique per user. */
  openId: varchar("openId", { length: 64 }).notNull().unique(),
  name: text("name"),
  email: varchar("email", { length: 320 }),
  loginMethod: varchar("loginMethod", { length: 64 }),
  role: mysqlEnum("role", ["user", "admin"]).default("user").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
  lastSignedIn: timestamp("lastSignedIn").defaultNow().notNull(),
});

export type User = typeof users.$inferSelect;
export type InsertUser = typeof users.$inferInsert;

export const priceAlerts = mysqlTable("price_alerts", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  offerId: int("offerId").notNull(),
  productName: varchar("productName", { length: 500 }).notNull(),
  threshold: decimal("threshold", { precision: 12, scale: 2 }).notNull(),
  currency: varchar("currency", { length: 3 }).notNull(),
  status: mysqlEnum("status", ["active", "paused"]).default("active").notNull(),
  clientCreatedAt: timestamp("clientCreatedAt").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => ({
  userOfferUnique: uniqueIndex("price_alerts_user_offer_unique").on(table.userId, table.offerId),
}));

export const pushDevices = mysqlTable("push_devices", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  expoToken: varchar("expoToken", { length: 255 }).notNull(),
  platform: mysqlEnum("platform", ["ios", "android"]).notNull(),
  permission: mysqlEnum("permission", ["granted", "denied"]).notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => ({
  tokenUnique: uniqueIndex("push_devices_token_unique").on(table.expoToken),
}));

export type PriceAlert = typeof priceAlerts.$inferSelect;
export type InsertPriceAlert = typeof priceAlerts.$inferInsert;

export const savedCollections = mysqlTable("saved_collections", {
  id: int("id").autoincrement().primaryKey(),
  userId: int("userId").notNull(),
  clientId: varchar("clientId", { length: 96 }).notNull(),
  name: varchar("name", { length: 42 }).notNull(),
  clientCreatedAt: timestamp("clientCreatedAt").notNull(),
  clientUpdatedAt: timestamp("clientUpdatedAt").notNull(),
  deletedAt: timestamp("deletedAt"),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
  updatedAt: timestamp("updatedAt").defaultNow().onUpdateNow().notNull(),
}, (table) => ({
  userClientUnique: uniqueIndex("saved_collections_user_client_unique").on(table.userId, table.clientId),
}));

export const savedCollectionMembers = mysqlTable("saved_collection_members", {
  id: int("id").autoincrement().primaryKey(),
  collectionId: int("collectionId").notNull(),
  offerId: int("offerId").notNull(),
  createdAt: timestamp("createdAt").defaultNow().notNull(),
}, (table) => ({
  collectionOfferUnique: uniqueIndex("saved_collection_members_collection_offer_unique").on(table.collectionId, table.offerId),
}));

export type SavedCollection = typeof savedCollections.$inferSelect;
