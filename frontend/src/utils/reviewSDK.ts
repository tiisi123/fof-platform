type ReviewSDKWindow = Window & {
  ReviewSDK?: {
    initReviewSDK: () => unknown
  }
  __reviewSDK__?: unknown
}

/**
 * Initialize review SDK once. Safe to call multiple times.
 */
export const initReviewSDK = (): void => {
  if (typeof window === 'undefined') {
    return
  }

  const w = window as ReviewSDKWindow
  if (w.__reviewSDK__) {
    return
  }

  if (!w.ReviewSDK || typeof w.ReviewSDK.initReviewSDK !== 'function') {
    console.warn(
      '[ReviewSDK] SDK not loaded, please check review-sdk.umd.js accessibility.',
    )
    return
  }

  try {
    w.__reviewSDK__ = w.ReviewSDK.initReviewSDK()
    console.log('[ReviewSDK] initialized')
  } catch (error) {
    console.error('[ReviewSDK] init failed:', error)
  }
}
