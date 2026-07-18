/* FILON — background service worker (MV3).
   Seeds default stats on install. In production this is where API tokens,
   affiliate-link resolution and saved-savings accounting would live. */
chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.get({ active: null }, (cur) => {
    if (cur.active === null) {
      chrome.storage.local.set({
        active: true,
        monthSaved: 0,
        totalSaved: 0,
        filonCount: 0,
      });
    }
  });
});
