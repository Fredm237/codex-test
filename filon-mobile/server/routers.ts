import { COOKIE_NAME } from "../shared/const.js";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { protectedProcedure, publicProcedure, router } from "./_core/trpc";
import * as db from "./db";
import { z } from "zod";
import { analyzeRecreateInspiration } from "./recreate";

const priceAlertSchema = z.object({
  offerId: z.number().int().positive(),
  name: z.string().trim().min(1).max(500),
  threshold: z.number().positive().finite(),
  currency: z.string().trim().length(3),
  createdAt: z.string().datetime(),
});

const savedCollectionSchema = z.object({
  clientId: z.string().trim().min(1).max(96),
  name: z.string().trim().min(1).max(42),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
  deletedAt: z.string().datetime().nullable(),
  offerIds: z.array(z.number().int().positive()).max(500),
});

export const appRouter = router({
  system: systemRouter,
  auth: router({
    me: publicProcedure.query((opts) => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return { success: true } as const;
    }),
  }),

  alerts: router({
    list: protectedProcedure.query(({ ctx }) => db.getUserPriceAlerts(ctx.user.id)),
    sync: protectedProcedure
      .input(z.object({ alerts: z.array(priceAlertSchema).max(100) }))
      .mutation(({ ctx, input }) => db.syncUserPriceAlerts(ctx.user.id, input.alerts)),
    registerDevice: protectedProcedure
      .input(z.object({
        expoToken: z.string().trim().min(1).max(255),
        platform: z.enum(["ios", "android"]),
        permission: z.enum(["granted", "denied"]),
      }))
      .mutation(({ ctx, input }) => db.registerPushDevice(ctx.user.id, input)),
  }),

  collections: router({
    list: protectedProcedure.query(({ ctx }) => db.getUserSavedCollections(ctx.user.id)),
    sync: protectedProcedure
      .input(z.object({ collections: z.array(savedCollectionSchema).max(100) }))
      .mutation(({ ctx, input }) => db.syncUserSavedCollections(ctx.user.id, input.collections)),
  }),

  recreate: router({
    analyze: publicProcedure
      .input(z.object({ imageUrl: z.string().trim().url().max(2_048) }))
      .mutation(({ input }) => analyzeRecreateInspiration(input.imageUrl)),
  }),
});

export type AppRouter = typeof appRouter;
