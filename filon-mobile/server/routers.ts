import { COOKIE_NAME } from "../shared/const.js";
import { getSessionCookieOptions } from "./_core/cookies";
import { systemRouter } from "./_core/systemRouter";
import { protectedProcedure, publicProcedure, router } from "./_core/trpc";
import * as db from "./db";
import { z } from "zod";
import { analyzeRecreateInspiration } from "./recreate";

export const appRouter = router({
  // if you need to use socket.io, read and register route in server/_core/index.ts, all api should start with '/api/' so that the gateway can route correctly
  system: systemRouter,
  auth: router({
    me: publicProcedure.query((opts) => opts.ctx.user),
    logout: publicProcedure.mutation(({ ctx }) => {
      const cookieOptions = getSessionCookieOptions(ctx.req);
      ctx.res.clearCookie(COOKIE_NAME, { ...cookieOptions, maxAge: -1 });
      return {
        success: true,
      } as const;
    }),
  }),

  alerts: router({
    list: protectedProcedure.query(({ ctx }) => db.getUserPriceAlerts(ctx.user.id)),
    sync: protectedProcedure.input(z.object({ alerts: z.array(z.object({ offerId: z.number().int().positive(), name: z.string().trim().min(1).max(500), threshold: z.number().positive().finite(), currency: z.string().trim().length(3), createdAt: z.string().datetime() })).max(100) })).mutation(({ ctx, input }) => db.syncUserPriceAlerts(ctx.user.id, input.alerts)),
    registerDevice: protectedProcedure.input(z.object({ expoToken: z.string().trim().min(1).max(255), platform: z.enum(["ios", "android"]), permission: z.enum(["granted", "denied"]) })).mutation(({ ctx, input }) => db.registerPushDevice(ctx.user.id, input)),
  }),

  collections: router({
    list: protectedProcedure.query(({ ctx }) => db.getUserSavedCollections(ctx.user.id)),
    sync: protectedProcedure.input(z.object({ collections: z.array(z.object({ clientId: z.string().trim().min(1).max(96), name: z.string().trim().min(1).max(42), createdAt: z.string().datetime(), updatedAt: z.string().datetime(), deletedAt: z.string().datetime().nullable(), offerIds: z.array(z.number().int().positive()).max(500) })).max(100) })).mutation(({ ctx, input }) => db.syncUserSavedCollections(ctx.user.id, input.collections)),
  }),

  recreate: router({
    analyze: publicProcedure.input(z.object({ imageUrl: z.string().trim().min(1).max(8_000_000) })).mutation(({ input }) => analyzeRecreateInspiration(input.imageUrl)),
  }),

  // TODO: add feature routers here, e.g.
  // todo: router({
  //   list: protectedProcedure.query(({ ctx }) =>
  //     db.getUserTodos(ctx.user.id)
  //   ),
  // }),
});

export type AppRouter = typeof appRouter;
