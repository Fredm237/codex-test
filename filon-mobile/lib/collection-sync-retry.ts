export type CollectionRetryInput = {
  authenticated: boolean;
  pendingSync: boolean;
  pushRegistrationFailed?: boolean;
  internetReachable: boolean;
  syncing: boolean;
};

export function shouldAutoRetryCollectionSync(input: CollectionRetryInput) {
  return input.authenticated && (input.pendingSync || input.pushRegistrationFailed === true) && input.internetReachable && !input.syncing;
}
