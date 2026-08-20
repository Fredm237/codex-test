export type CollectionRetryInput = {
  authenticated: boolean;
  pendingSync: boolean;
  internetReachable: boolean;
  syncing: boolean;
};

export function shouldAutoRetryCollectionSync(input: CollectionRetryInput) {
  return input.authenticated && input.pendingSync && input.internetReachable && !input.syncing;
}
