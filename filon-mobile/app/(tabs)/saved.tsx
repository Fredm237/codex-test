import MaterialIcons from "@expo/vector-icons/MaterialIcons";
import { useRouter } from "expo-router";
import { useCallback, useEffect, useRef, useState } from "react";
import { ActivityIndicator, FlatList, Pressable, StyleSheet, Text, View } from "react-native";
import * as Network from "expo-network";

import { OfferCard } from "@/components/filon/offer-card";
import { Eyebrow, TactileButton } from "@/components/filon/filon-ui";
import { ScreenContainer } from "@/components/screen-container";
import { useFavorites } from "@/hooks/use-favorites";
import { useColors } from "@/hooks/use-colors";
import { useLocalAlerts } from "@/hooks/use-local-alerts";
import { useAuth } from "@/hooks/use-auth";
import { groupFavoriteRows } from "@/lib/favorite-groups";
import { ObservedPriceSignal } from "@/components/filon/observed-price-signal";
import { useFavoriteCollections } from "@/hooks/use-favorite-collections";
import { formatFilonPrice } from "@/lib/filon-api";
import { startOAuthLogin } from "@/constants/oauth";
import { useLocale } from "@/lib/locale";
import { requestPushRegistration } from "@/lib/push-registration";
import { haptic } from "@/lib/haptics";
import { useSyncRetryQueue } from "@/hooks/use-sync-retry-queue";
import { useFollowUpTimeline } from "@/hooks/use-follow-up-timeline";
import { FollowUpTimeline } from "@/components/filon/follow-up-timeline";
import { recordFollowUpEvent } from "@/lib/follow-up-timeline";
import { trpc } from "@/lib/trpc";
import { usePurchaseIntents } from "@/hooks/use-purchase-intents";
import { getPurchaseIntentCatalogueParams, type PurchaseIntent } from "@/lib/purchase-intents";
import { useIntentOfferEvidence } from "@/hooks/use-intent-offer-evidence";
import { isIntentOfferEvidenceCurrent, type IntentOfferEvidence } from "@/lib/intent-offer-evidence";
import { useIntentDecisionJournal } from "@/hooks/use-intent-decision-journal";
import { IntentDecisionTimeline } from "@/components/filon/intent-decision-timeline";
import { useFilonEvidenceNow } from "@/hooks/use-filon-evidence-now";
import { shouldAutoRetryCollectionSync } from "@/lib/collection-sync-retry";
import { confirmPushRegistration } from "@/lib/push-sync";
import { runSingleFlight } from "@/lib/single-flight";

export default function SavedScreen() {
  const router = useRouter();
  const { locale, t } = useLocale();
  const colors = useColors();
  const styles = createStyles(colors);
  const favorites = useFavorites();
  const alerts = useLocalAlerts();
  const collections = useFavoriteCollections();
  const auth = useAuth();
  const syncMutation = trpc.alerts.sync.useMutation();
  const collectionMutation = trpc.collections.sync.useMutation();
  const deviceMutation = trpc.alerts.registerDevice.useMutation();
  const retryQueue = useSyncRetryQueue();
  const timeline = useFollowUpTimeline();
  const intents = usePurchaseIntents();
  const linkedOffers = useIntentOfferEvidence();
  const alertItems = alerts.items;
  const alertsPendingSync = alerts.pendingSync;
  const markAlertsReconciled = alerts.markReconciled;
  const syncAlerts = syncMutation.mutateAsync;
  const syncCollections = collectionMutation.mutateAsync;
  const registerDevice = deviceMutation.mutateAsync;
  const buildCollectionsPayload = collections.syncPayload;
  const mergeRemoteCollections = collections.mergeRemote;
  const clearSyncRetry = retryQueue.clear;
  const recordSyncFailure = retryQueue.recordFailure;
  const refreshTimeline = timeline.refresh;
  const collectionsPendingSync = collections.pendingSync;
  const nextRetryAt = retryQueue.nextRetryAt;
  const [autoRetrying, setAutoRetrying] = useState(false);
  const [reconcilePending, setReconcilePending] = useState(false);
  const reconcileFlight = useRef<Promise<void> | null>(null);
  const [pushState, setPushState] = useState<"idle" | "granted" | "denied" | "unavailable" | "failed">("idle");
  const copy = {
    fr: { device: "Enregistré sur cet appareil.", alertCount: "seuil local", alertCountPlural: "seuils locaux", threshold: "Seuil local", status: "Local · prêt à synchroniser", remove: "Supprimer ce seuil", removeFavorite: "Retirer des favoris", addCollection: "Ajouter à une collection", uncategorized: "Autres suivis", connect: "Connecter mon compte", syncing: "Synchronisation…", retrying: "Reprise de synchronisation…", syncNow: "Synchroniser mes suivis", synced: "Suivis synchronisés avec votre compte", pending: "Modifications de suivis en attente", lastSync: "Dernière synchronisation :", syncFailed: "La synchronisation a échoué. Réessayez.", pushReady: "Appareil enregistré. Une alerte distante dépend encore du contrôle serveur du prix.", pushDenied: "Notifications non autorisées sur cet appareil.", pushUnavailable: "Notifications push disponibles après installation native.", pushFailed: "Canal de notification à réessayer.", sync: "Les seuils et collections sont synchronisés après connexion ; les notifications push restent proposées depuis un appareil compatible.", open: "Voir l’offre chez", stock: "En stock", unavailable: "Indisponible", unknown: "À confirmer", priceToCheck: "Prix à confirmer", savedCount: "offres suivies", browse: "Explorer de nouvelles offres", browseHint: "Revenir au catalogue", intents: "Intentions d’achat", intentLocal: "Règle enregistrée sur cet appareil", editIntent: "Modifier", exploreIntent: "Explorer", illuminateIntent: "Éclairer", chooseOffer: "Choisir une offre pour une alerte", alertRuleHint: "Une alerte de prix nécessite une offre exacte et un seuil choisi." },
    nl: { device: "Op dit apparaat opgeslagen.", alertCount: "lokale drempel", alertCountPlural: "lokale drempels", threshold: "Lokale drempel", status: "Lokaal · klaar om te synchroniseren", remove: "Deze drempel verwijderen", removeFavorite: "Uit favorieten verwijderen", addCollection: "Aan collectie toevoegen", uncategorized: "Andere gevolgde items", connect: "Mijn account verbinden", syncing: "Synchroniseren…", retrying: "Synchronisatie wordt hervat…", syncNow: "Mijn gevolgde items synchroniseren", synced: "Gevolgde items gesynchroniseerd met je account", pending: "Wijzigingen aan gevolgde items wachten", lastSync: "Laatst gesynchroniseerd:", syncFailed: "Synchronisatie is mislukt. Probeer opnieuw.", pushReady: "Apparaat geregistreerd. Een externe melding hangt nog af van de prijscontrole op de server.", pushDenied: "Meldingen zijn niet toegestaan op dit apparaat.", pushUnavailable: "Pushmeldingen zijn beschikbaar na native installatie.", pushFailed: "Meldingskanaal opnieuw proberen.", sync: "Drempels en collecties worden na aanmelding gesynchroniseerd; pushmeldingen blijven beschikbaar op een compatibel apparaat.", open: "Bekijk aanbieding bij", stock: "Op voorraad", unavailable: "Niet beschikbaar", unknown: "Te bevestigen", priceToCheck: "Prijs te bevestigen", savedCount: "gevolgde aanbiedingen", browse: "Nieuwe aanbiedingen ontdekken", browseHint: "Terug naar catalogus", intents: "Aankoopintenties", intentLocal: "Regel op dit apparaat opgeslagen", editIntent: "Wijzigen", exploreIntent: "Verkennen", illuminateIntent: "Verkennen met Assistent", chooseOffer: "Kies een aanbod voor een melding", alertRuleHint: "Een prijswaarschuwing vereist een exact aanbod en gekozen drempel." },
    en: { device: "Saved on this device.", alertCount: "local threshold", alertCountPlural: "local thresholds", threshold: "Local threshold", status: "Local · ready to sync", remove: "Remove this threshold", removeFavorite: "Remove from saved", addCollection: "Add to collection", uncategorized: "Other saved items", connect: "Connect my account", syncing: "Synchronizing…", retrying: "Resuming synchronization…", syncNow: "Sync my saved items", synced: "Saved items synced with your account", pending: "Saved-item changes waiting to sync", lastSync: "Last synchronized:", syncFailed: "Synchronization failed. Try again.", pushReady: "Device registered. A remote alert still depends on server-side price checking.", pushDenied: "Notifications are not allowed on this device.", pushUnavailable: "Push notifications become available after native installation.", pushFailed: "Notification channel needs another try.", sync: "Price thresholds and collections sync after sign-in; push notifications remain available from a compatible device.", open: "View offer at", stock: "In stock", unavailable: "Unavailable", unknown: "To confirm", priceToCheck: "Price to confirm", savedCount: "followed offers", browse: "Explore new offers", browseHint: "Back to catalogue", intents: "Purchase intents", intentLocal: "Rule saved on this device", editIntent: "Edit", exploreIntent: "Explore", illuminateIntent: "Explore with Assistant", chooseOffer: "Choose an offer for an alert", alertRuleHint: "A price alert requires one exact offer and a chosen threshold." },
  }[locale];
  const evidenceCopy = {
    fr: { linkedOffer: "Offre retenue", unlinkOffer: "Retirer le lien", alertForOffer: "Alerter cette offre", priceUnknown: "Prix non confirmé", staleEvidence: "Relevé expiré : actualisez l’offre avant de créer une alerte." },
    nl: { linkedOffer: "Gekozen aanbod", unlinkOffer: "Koppeling verwijderen", alertForOffer: "Dit aanbod melden", priceUnknown: "Prijs niet bevestigd", staleEvidence: "Meting verlopen: vernieuw het aanbod voordat u een melding maakt." },
    en: { linkedOffer: "Selected offer", unlinkOffer: "Remove link", alertForOffer: "Alert for this offer", priceUnknown: "Price not confirmed", staleEvidence: "Observation expired: refresh the offer before creating an alert." },
  }[locale];
  const hasSyncableItems = alerts.items.length > 0 || collections.collections.length > 0 || Object.keys(collections.tombstones).length > 0;
  const syncState = !auth.isAuthenticated ? "needs-account" : reconcilePending || syncMutation.isPending || collectionMutation.isPending ? "syncing" : syncMutation.isError || collectionMutation.isError ? "failed" : collectionsPendingSync || alertsPendingSync || (!collections.lastSyncedAt && !alerts.lastSyncedAt) ? "pending" : "synced";
  const lastWatchSync = collections.lastSyncedAt ?? alerts.lastSyncedAt;
  const network = Network.useNetworkState();
  const rows = groupFavoriteRows(favorites.items, copy.uncategorized);
  const reconcile = useCallback((requestPush: boolean) => runSingleFlight(reconcileFlight, async () => {
      const collectionsPayload = buildCollectionsPayload();
      const alertsPayload = alertItems.map((alert) => ({ offerId: alert.offerId, name: alert.name, threshold: alert.threshold, currency: alert.currency, createdAt: alert.createdAt }));
      const remoteCollections = await syncCollections({ collections: collectionsPayload });
      await syncAlerts({ alerts: alertsPayload });
      if (requestPush) {
        try {
          const registration = await requestPushRegistration();
          const registrationStatus = await confirmPushRegistration(registration, registerDevice);
          if (registrationStatus === "failed") throw new Error("push-registration-failed");
          setPushState(registrationStatus);
        } catch (registrationError) {
          setPushState("failed");
          throw registrationError;
        }
      }
      await mergeRemoteCollections(remoteCollections, collectionsPayload);
      await markAlertsReconciled(alertsPayload);
      haptic.success();
      await recordFollowUpEvent("sync-succeeded", "FILON");
      await refreshTimeline();
      await clearSyncRetry();
    }, setReconcilePending), [alertItems, buildCollectionsPayload, clearSyncRetry, markAlertsReconciled, mergeRemoteCollections, refreshTimeline, registerDevice, syncAlerts, syncCollections]);
  const connectOrSync = async () => {
    if (!auth.isAuthenticated) { await startOAuthLogin(); return; }
    try { await reconcile(true); } catch { await recordSyncFailure(); }
  };
  useEffect(() => {
    const retryPushRegistration = pushState === "failed";
    const shouldRetry = shouldAutoRetryCollectionSync({
      authenticated: auth.isAuthenticated,
      pendingSync: collectionsPendingSync || alertsPendingSync,
      pushRegistrationFailed: retryPushRegistration,
      internetReachable: network.isInternetReachable === true,
      syncing: reconcilePending || autoRetrying || collectionMutation.isPending || syncMutation.isPending,
    });
    if (!shouldRetry) return;
    const now = Date.now();
    const target = nextRetryAt ? Date.parse(nextRetryAt) : now;
    const timeout = setTimeout(() => {
      setAutoRetrying(true);
      void reconcile(retryPushRegistration)
        .catch(() => recordSyncFailure())
        .finally(() => setAutoRetrying(false));
    }, Math.max(0, target - now));
    return () => clearTimeout(timeout);
  }, [alertsPendingSync, auth.isAuthenticated, autoRetrying, collectionMutation.isPending, collectionsPendingSync, network.isInternetReachable, nextRetryAt, pushState, reconcile, reconcilePending, recordSyncFailure, syncMutation.isPending]);
  const syncLabel = syncState === "needs-account" ? copy.connect : syncState === "syncing" || autoRetrying || nextRetryAt ? copy.retrying : copy.syncNow;
  return (
    <ScreenContainer className="" containerClassName="bg-background">
      <FlatList
        data={rows}
        keyExtractor={(item) => item.key}
        contentContainerStyle={styles.content}
        ListHeaderComponent={<><Eyebrow>FILON</Eyebrow><Text style={styles.title}>{t.saved}</Text><Text style={styles.caption}>{copy.device} {alerts.items.length > 0 ? `${alerts.items.length} ${alerts.items.length > 1 ? copy.alertCountPlural : copy.alertCount} — ` : ""}{copy.sync}</Text><View style={styles.summaryRow}><View style={styles.summaryCard}><MaterialIcons name="bookmark" size={19} color="#C89544" /><View><Text style={styles.summaryValue}>{favorites.items.length}</Text><Text style={styles.summaryLabel}>{copy.savedCount}</Text></View></View><Pressable accessibilityRole="button" accessibilityLabel={copy.browse} onPress={() => router.push("/(tabs)/catalogue")} style={({ pressed }) => [styles.browseCard, pressed && styles.pressed]}><MaterialIcons name="explore" size={19} color="#0E0C0B" /><View style={{ flex: 1 }}><Text style={styles.browseText}>{copy.browse}</Text><Text style={styles.browseHint}>{copy.browseHint}</Text></View><MaterialIcons name="arrow-forward" size={17} color="#0E0C0B" /></Pressable></View>{intents.items.length > 0 ? <View style={styles.intentSection}><Text style={styles.intentSectionTitle}>{copy.intents}</Text>{intents.items.map((intent) => <IntentWatchCard key={intent.id} intent={intent} evidence={linkedOffers.forIntent(intent.id)} locale={locale} copy={copy} evidenceCopy={evidenceCopy} colors={colors} styles={styles} onEdit={() => router.push({ pathname: "/intent/[id]", params: { id: intent.id } } as never)} onExplore={() => router.push({ pathname: "/catalogue/search", params: getPurchaseIntentCatalogueParams(intent) } as never)} onIlluminate={() => router.push({ pathname: "/(tabs)/assistant", params: { intentId: intent.id } } as never)} />)}</View> : null}{hasSyncableItems ? <View style={styles.syncCard}>{syncState === "synced" ? <><MaterialIcons name="cloud-done" size={20} color="#8FB072" /><View style={styles.syncCopy}><Text style={styles.syncSuccess}>{copy.synced}</Text>{lastWatchSync ? <Text style={styles.syncBody}>{copy.lastSync} {new Intl.DateTimeFormat(locale, { dateStyle: "medium", timeStyle: "short" }).format(new Date(lastWatchSync))}</Text> : null}{pushState !== "idle" ? <Text style={styles.syncBody}>{pushState === "granted" ? copy.pushReady : pushState === "denied" ? copy.pushDenied : pushState === "unavailable" ? copy.pushUnavailable : copy.pushFailed}</Text> : null}</View></> : <><MaterialIcons name={syncState === "failed" ? "sync-problem" : "cloud-upload"} size={20} color="#C89544" /><View style={styles.syncCopy}><Text style={styles.syncTitle}>{syncState === "failed" ? copy.syncFailed : autoRetrying ? copy.retrying : syncState === "pending" ? copy.pending : auth.isAuthenticated ? auth.user?.name ?? copy.syncNow : copy.connect}</Text><Text style={styles.syncBody}>{copy.sync}</Text></View><Pressable disabled={reconcilePending || syncMutation.isPending || collectionMutation.isPending} accessibilityRole="button" accessibilityLabel={syncLabel} onPress={() => void connectOrSync()} style={({ pressed }) => [styles.syncButton, (pressed || reconcilePending || syncMutation.isPending || collectionMutation.isPending) && styles.pressed]}><Text style={styles.syncButtonText}>{syncLabel}</Text></Pressable></>}</View> : null}</>}
        renderItem={({ item }) => { if (item.type === "heading") return <Text style={styles.groupHeading}>{item.category}</Text>; const offer = item.offer; const alert = alerts.findByOfferId(offer.id); const offerCollections = collections.forOffer(offer.id); return <View><OfferCard offer={{ ...offer, brand: null, merchantSlug: null }} price={formatFilonPrice(offer.price, locale, offer.currency)} priceToCheckLabel={copy.priceToCheck} openLabel={copy.open} inStockLabel={copy.stock} unavailableLabel={copy.unavailable} unknownLabel={copy.unknown} onPress={() => router.push({ pathname: "/product/[id]", params: { id: String(offer.id), name: offer.name, price: String(offer.price), currency: offer.currency, merchant: offer.merchantName, image: offer.imageUrl ?? "", link: offer.link, stock: offer.inStock === true ? "1" : offer.inStock === false ? "0" : "unknown", observedAt: offer.observedAt ?? "", evidenceCurrent: offer.evidenceCurrent ? "1" : "0", category: offer.category ?? "" } } as never)} /><ObservedPriceSignal offerId={offer.id} locale={locale} />{offerCollections.length > 0 ? <Text style={styles.collectionNames}>{offerCollections.map((collection) => collection.name).join(" · ")}</Text> : null}{alert ? <View style={styles.threshold}><MaterialIcons name="notifications-none" size={16} color={colors.primary} /><View style={styles.thresholdMeta}><Text style={styles.thresholdText}>{copy.threshold} : {formatFilonPrice(alert.threshold, locale, alert.currency)}</Text><Text style={styles.status}>{copy.status}</Text></View><Pressable accessibilityRole="button" accessibilityLabel={copy.remove} onPress={() => void alerts.remove(offer.id)} style={({ pressed }) => [styles.remove, pressed && styles.removePressed]}><MaterialIcons name="close" size={17} color={colors.foreground} /></Pressable></View> : <Pressable accessibilityRole="button" accessibilityLabel={copy.removeFavorite} onPress={() => void favorites.toggle(offer)} style={({ pressed }) => [styles.removeFavorite, pressed && styles.removePressed]}><MaterialIcons name="bookmark-remove" size={16} color={colors.primary} /><Text style={styles.removeFavoriteText}>{copy.removeFavorite}</Text></Pressable>}<Pressable accessibilityRole="button" accessibilityLabel={copy.addCollection} onPress={() => router.push({ pathname: "/collection/manage", params: { offerId: String(offer.id) } } as never)} style={({ pressed }) => [styles.collectionAction, pressed && styles.removePressed]}><MaterialIcons name="folder-open" size={16} color={colors.primary} /><Text style={styles.collectionActionText}>{copy.addCollection}</Text></Pressable></View>; }}
        ItemSeparatorComponent={() => <View style={{ height: 10 }} />}
        ListFooterComponent={<FollowUpTimeline events={timeline.events} locale={locale} onClear={() => void timeline.clear()} />}
        ListEmptyComponent={intents.items.length > 0 ? null : <View style={styles.empty}>{!favorites.ready ? <ActivityIndicator color={colors.primary} /> : <><View style={styles.icon}><MaterialIcons name="bookmark" size={26} color={colors.primary} /></View><Text style={styles.emptyTitle}>{t.noSavedTitle}</Text><Text style={styles.emptyBody}>{t.noSavedBody}</Text><TactileButton accessibilityLabel={t.exploreCatalogue} onPress={() => router.push("/(tabs)/catalogue")} style={styles.action}><Text style={styles.actionText}>{t.exploreCatalogue}</Text></TactileButton></>}</View>}
      />
    </ScreenContainer>
  );
}

function IntentWatchCard({ intent, evidence, locale, copy, evidenceCopy, colors, styles, onEdit, onExplore, onIlluminate }: { intent: PurchaseIntent; evidence: IntentOfferEvidence | null; locale: "fr" | "nl" | "en"; copy: { intentLocal: string; editIntent: string; exploreIntent: string; illuminateIntent: string; chooseOffer: string; alertRuleHint: string }; evidenceCopy: { linkedOffer: string; unlinkOffer: string; alertForOffer: string; priceUnknown: string; staleEvidence: string }; colors: ReturnType<typeof useColors>; styles: ReturnType<typeof createStyles>; onEdit: () => void; onExplore: () => void; onIlluminate: () => void }) {
  const budget = intent.maxBudget === null ? null : `${intent.maxBudget.toLocaleString(locale === "nl" ? "nl-BE" : locale === "fr" ? "fr-BE" : "en-BE", { maximumFractionDigits: 2 })} EUR`;
  const links = useIntentOfferEvidence();
  const journal = useIntentDecisionJournal();
  const router = useRouter();
  const linked = links.ready ? links.forIntent(intent.id) : evidence;
  const evidenceNow = useFilonEvidenceNow([linked?.observedAt]);
  const alertIsCurrent = linked !== null && isIntentOfferEvidenceCurrent(linked, evidenceNow);
  const linkedPrice = linked && alertIsCurrent ? formatFilonPrice(linked.price, locale, linked.currency) : evidenceCopy.priceUnknown;
  const removeLink = () => { void links.unlink(intent.id).then(() => journal.record(intent.id, "offer-unlinked", linked?.name ?? intent.need)).then(() => haptic.light()); };
  const createAlert = (linkedOffer: IntentOfferEvidence) => {
    if (!isIntentOfferEvidenceCurrent(linkedOffer, evidenceNow)) return;
    router.push({ pathname: "/alert/new", params: { id: String(linkedOffer.offerId), name: linkedOffer.name, price: String(linkedOffer.price), currency: linkedOffer.currency, intentId: intent.id, observedAt: linkedOffer.observedAt ?? "", evidenceCurrent: linkedOffer.evidenceCurrent ? "1" : "0" } } as never);
  };
  const explore = () => { void journal.record(intent.id, "catalogue-explored", intent.need); onExplore(); };
  const illuminate = () => { void journal.record(intent.id, "assistant-opened", intent.need); onIlluminate(); };
  return (
    <View style={styles.intentCard}>
      <View style={styles.intentTop}>
        <View style={styles.intentIcon}><MaterialIcons name="track-changes" size={18} color={colors.primary} /></View>
        <View style={styles.intentWords}><Text numberOfLines={2} style={styles.intentNeed}>{intent.need}</Text><Text style={styles.intentStatus}>{copy.intentLocal}</Text></View>
        <Pressable accessibilityRole="button" accessibilityLabel={copy.editIntent} onPress={onEdit} style={({ pressed }) => [styles.intentEdit, pressed && styles.removePressed]}><MaterialIcons name="edit" size={17} color={colors.primary} /></Pressable>
      </View>
      {budget || intent.deadline || intent.preferences ? <View style={styles.intentMeta}>{budget ? <Text style={styles.intentMetaText}>{budget}</Text> : null}{intent.deadline ? <Text style={styles.intentMetaText}>{intent.deadline}</Text> : null}{intent.preferences ? <Text numberOfLines={1} style={styles.intentMetaText}>{intent.preferences}</Text> : null}</View> : null}
      <View style={styles.intentActions}>
        <Pressable accessibilityRole="button" accessibilityLabel={copy.exploreIntent} onPress={explore} style={({ pressed }) => [styles.intentAction, pressed && styles.removePressed]}><MaterialIcons name="search" size={16} color={colors.primary} /><Text style={styles.intentActionText}>{copy.exploreIntent}</Text></Pressable>
        <Pressable accessibilityRole="button" accessibilityLabel={copy.illuminateIntent} onPress={illuminate} style={({ pressed }) => [styles.intentAction, pressed && styles.removePressed]}><MaterialIcons name="auto-awesome" size={16} color={colors.primary} /><Text style={styles.intentActionText}>{copy.illuminateIntent}</Text></Pressable>
      </View>
      {linked ? (
        <View style={styles.alertLead}>
          <MaterialIcons name={alertIsCurrent ? "verified" : "history"} size={16} color={alertIsCurrent ? colors.success : colors.warning} />
          <View style={styles.alertLeadWords}><Text style={styles.alertLeadTitle}>{evidenceCopy.linkedOffer}</Text><Text numberOfLines={3} style={styles.alertLeadBody}>{linked.name} · {linkedPrice} · {linked.merchantName}{alertIsCurrent ? "" : `\n${evidenceCopy.staleEvidence}`}</Text></View>
          <Pressable accessibilityRole="button" accessibilityLabel={evidenceCopy.unlinkOffer} onPress={removeLink} style={({ pressed }) => [styles.intentEdit, pressed && styles.removePressed]}><MaterialIcons name="close" size={16} color={colors.muted} /></Pressable>
          <Pressable accessibilityRole="button" accessibilityLabel={alertIsCurrent ? evidenceCopy.alertForOffer : evidenceCopy.staleEvidence} accessibilityState={{ disabled: !alertIsCurrent }} disabled={!alertIsCurrent} onPress={() => createAlert(linked)} style={({ pressed }) => [styles.alertLeadAction, !alertIsCurrent && styles.alertLeadActionDisabled, pressed && styles.removePressed]}><MaterialIcons name="notifications-none" size={17} color={colors.background} /></Pressable>
        </View>
      ) : (
        <View style={styles.alertLead}>
          <MaterialIcons name="notifications-none" size={16} color={colors.warning} />
          <View style={styles.alertLeadWords}><Text style={styles.alertLeadTitle}>{copy.chooseOffer}</Text><Text style={styles.alertLeadBody}>{copy.alertRuleHint}</Text></View>
          <Pressable accessibilityRole="button" accessibilityLabel={copy.chooseOffer} onPress={explore} style={({ pressed }) => [styles.alertLeadAction, pressed && styles.removePressed]}><MaterialIcons name="arrow-forward" size={18} color={colors.background} /></Pressable>
        </View>
      )}
      <IntentDecisionTimeline events={journal.forIntent(intent.id)} locale={locale} onClear={() => void journal.clear(intent.id)} />
    </View>
  );
}

function createStyles(colors: ReturnType<typeof useColors>) { return StyleSheet.create({ content: { flexGrow: 1, padding: 20, paddingBottom: 116 }, title: { color: colors.foreground, fontSize: 34, fontWeight: "800", letterSpacing: -0.8, marginTop: 6 }, caption: { color: colors.muted, fontSize: 13, lineHeight: 19, marginTop: 7, marginBottom: 13 }, summaryRow: { flexDirection: "row", gap: 10, marginBottom: 13 }, summaryCard: { width: 106, minHeight: 72, padding: 12, borderRadius: 18, justifyContent: "space-between", backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, summaryValue: { color: colors.foreground, fontSize: 19, fontWeight: "900", marginTop: 5 }, summaryLabel: { color: colors.muted, fontSize: 10, fontWeight: "700", marginTop: 1 }, browseCard: { flex: 1, minHeight: 72, paddingHorizontal: 12, borderRadius: 18, flexDirection: "row", alignItems: "center", gap: 9, backgroundColor: colors.primary }, browseText: { color: colors.background, fontSize: 12, fontWeight: "900" }, browseHint: { color: colors.background, opacity: 0.72, fontSize: 10, fontWeight: "700", marginTop: 2 }, intentSection: { gap: 9, marginBottom: 20 }, intentSectionTitle: { color: colors.primary, fontSize: 12, fontWeight: "900", letterSpacing: 0.6, textTransform: "uppercase", marginTop: 3 }, intentCard: { padding: 13, gap: 11, borderRadius: 20, borderWidth: 1, borderColor: colors.border, backgroundColor: colors.surface }, intentTop: { flexDirection: "row", alignItems: "center", gap: 10 }, intentIcon: { width: 38, height: 38, alignItems: "center", justifyContent: "center", borderRadius: 13, backgroundColor: `${colors.primary}14` }, intentWords: { flex: 1, minWidth: 0 }, intentNeed: { color: colors.foreground, fontSize: 14, lineHeight: 19, fontWeight: "900" }, intentStatus: { color: colors.muted, fontSize: 10, marginTop: 3, fontWeight: "700" }, intentEdit: { width: 38, height: 38, alignItems: "center", justifyContent: "center", borderRadius: 12, backgroundColor: colors.background }, intentMeta: { flexDirection: "row", flexWrap: "wrap", gap: 6 }, intentMetaText: { color: colors.muted, fontSize: 10, fontWeight: "700" }, intentActions: { flexDirection: "row", flexWrap: "wrap", gap: 7 }, intentAction: { minHeight: 36, paddingHorizontal: 10, alignItems: "center", flexDirection: "row", gap: 5, borderRadius: 12, backgroundColor: colors.background, borderWidth: 1, borderColor: colors.border }, intentActionText: { color: colors.primary, fontSize: 11, fontWeight: "800" }, alertLead: { minHeight: 54, padding: 9, flexDirection: "row", alignItems: "center", gap: 8, borderRadius: 14, backgroundColor: `${colors.warning}12`, borderWidth: 1, borderColor: `${colors.warning}34` }, alertLeadWords: { flex: 1, minWidth: 0 }, alertLeadTitle: { color: colors.foreground, fontSize: 11, fontWeight: "900" }, alertLeadBody: { color: colors.muted, marginTop: 2, fontSize: 9, lineHeight: 13, fontWeight: "600" }, alertLeadAction: { width: 34, height: 34, alignItems: "center", justifyContent: "center", borderRadius: 11, backgroundColor: colors.primary }, alertLeadActionDisabled: { opacity: 0.34 }, syncCard: { minHeight: 74, padding: 13, marginBottom: 22, borderRadius: 18, flexDirection: "row", alignItems: "center", gap: 9, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border }, syncCopy: { flex: 1 }, syncTitle: { color: colors.foreground, fontSize: 12, fontWeight: "800" }, syncBody: { color: colors.muted, fontSize: 10, lineHeight: 14, marginTop: 2 }, syncButton: { minHeight: 38, paddingHorizontal: 10, borderRadius: 12, alignItems: "center", justifyContent: "center", backgroundColor: colors.primary }, syncButtonText: { color: colors.background, fontSize: 10, fontWeight: "800", textAlign: "center" }, syncSuccess: { flex: 1, color: colors.success, fontSize: 12, fontWeight: "800" }, groupHeading: { color: colors.primary, fontSize: 12, fontWeight: "800", letterSpacing: 0.5, textTransform: "uppercase", marginTop: 9, marginBottom: 8 }, collectionNames: { minHeight: 31, paddingHorizontal: 12, paddingVertical: 8, marginTop: -2, color: colors.foreground, fontSize: 10, fontWeight: "700", borderWidth: 1, borderTopWidth: 0, borderColor: colors.border, backgroundColor: `${colors.primary}0E` }, threshold: { minHeight: 47, paddingLeft: 12, marginTop: -2, borderBottomLeftRadius: 15, borderBottomRightRadius: 15, flexDirection: "row", alignItems: "center", gap: 7, backgroundColor: `${colors.primary}17`, borderWidth: 1, borderTopWidth: 0, borderColor: `${colors.primary}38` }, thresholdMeta: { flex: 1, gap: 1 }, thresholdText: { color: colors.foreground, fontSize: 12, fontWeight: "700" }, status: { color: colors.muted, fontSize: 10, fontWeight: "600" }, remove: { width: 42, alignSelf: "stretch", alignItems: "center", justifyContent: "center" }, removeFavorite: { minHeight: 42, marginTop: -2, paddingHorizontal: 12, borderBottomLeftRadius: 15, borderBottomRightRadius: 15, flexDirection: "row", alignItems: "center", gap: 7, borderWidth: 1, borderTopWidth: 0, borderColor: colors.border, backgroundColor: colors.surface }, removeFavoriteText: { color: colors.primary, fontSize: 11, fontWeight: "800" }, collectionAction: { minHeight: 39, paddingHorizontal: 12, marginTop: -2, borderBottomLeftRadius: 15, borderBottomRightRadius: 15, flexDirection: "row", alignItems: "center", gap: 7, borderWidth: 1, borderTopWidth: 0, borderColor: colors.border, backgroundColor: colors.background }, collectionActionText: { color: colors.primary, fontSize: 11, fontWeight: "800" }, removePressed: { opacity: 0.58 }, empty: { flex: 1, minHeight: 420, alignItems: "center", justifyContent: "center", paddingHorizontal: 28, paddingBottom: 60 }, icon: { width: 60, height: 60, borderRadius: 20, alignItems: "center", justifyContent: "center", backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, marginBottom: 20 }, emptyTitle: { color: colors.foreground, textAlign: "center", fontSize: 22, fontWeight: "800" }, emptyBody: { color: colors.muted, textAlign: "center", fontSize: 14, lineHeight: 21, marginTop: 9, marginBottom: 24 }, action: { paddingHorizontal: 20, minHeight: 48, borderRadius: 16, backgroundColor: colors.primary }, actionText: { color: colors.background, fontSize: 14, fontWeight: "800" }, pressed: { opacity: 0.65 } }); }
