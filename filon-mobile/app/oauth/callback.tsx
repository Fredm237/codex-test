import { ThemedView } from "@/components/themed-view";
import * as Api from "@/lib/_core/api";
import * as Auth from "@/lib/_core/auth";
import * as Linking from "expo-linking";
import { useLocalSearchParams, useRouter } from "expo-router";
import { useEffect, useState } from "react";
import { ActivityIndicator, Text } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";

type CallbackValues = {
  code: string | null;
  state: string | null;
  hasProviderError: boolean;
};

function readCallbackValues(url: string): CallbackValues {
  try {
    const parsed = new URL(url, "http://localhost");
    return {
      code: parsed.searchParams.get("code"),
      state: parsed.searchParams.get("state"),
      hasProviderError: parsed.searchParams.has("error"),
    };
  } catch {
    return { code: null, state: null, hasProviderError: false };
  }
}

export default function OAuthCallback() {
  const router = useRouter();
  const params = useLocalSearchParams<{
    code?: string;
    state?: string;
    error?: string;
  }>();
  const [status, setStatus] = useState<"processing" | "success" | "error">("processing");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  useEffect(() => {
    const handleCallback = async () => {
      try {
        let code = params.code ?? null;
        let state = params.state ?? null;
        let hasProviderError = typeof params.error === "string";

        if (!code || !state) {
          const initialUrl = await Linking.getInitialURL();
          if (initialUrl) {
            const values = readCallbackValues(initialUrl);
            code = code ?? values.code;
            state = state ?? values.state;
            hasProviderError ||= values.hasProviderError;
          }
        }

        if (hasProviderError) {
          setStatus("error");
          setErrorMessage("The identity provider did not complete authentication.");
          return;
        }

        if (!code || !state) {
          setStatus("error");
          setErrorMessage("The authentication response is incomplete.");
          return;
        }

        const result = await Api.exchangeOAuthCode(code, state);
        if (!result.sessionToken) {
          setStatus("error");
          setErrorMessage("The secure session could not be created.");
          return;
        }

        await Auth.setSessionToken(result.sessionToken);
        if (result.user) {
          await Auth.setUserInfo({
            id: result.user.id,
            openId: result.user.openId,
            name: result.user.name,
            email: result.user.email,
            loginMethod: result.user.loginMethod,
            lastSignedIn: new Date(result.user.lastSignedIn || Date.now()),
          });
        }

        setStatus("success");
        setTimeout(() => router.replace("/(tabs)"), 1000);
      } catch {
        setStatus("error");
        setErrorMessage("Failed to complete authentication.");
      }
    };

    void handleCallback();
  }, [params.code, params.state, params.error, router]);

  return (
    <SafeAreaView className="flex-1" edges={["top", "bottom", "left", "right"]}>
      <ThemedView className="flex-1 items-center justify-center gap-4 p-5">
        {status === "processing" && (
          <>
            <ActivityIndicator size="large" />
            <Text className="mt-4 text-base leading-6 text-center text-foreground">
              Completing authentication...
            </Text>
          </>
        )}
        {status === "success" && (
          <>
            <Text className="text-base leading-6 text-center text-foreground">
              Authentication successful!
            </Text>
            <Text className="text-base leading-6 text-center text-foreground">
              Redirecting...
            </Text>
          </>
        )}
        {status === "error" && (
          <>
            <Text className="mb-2 text-xl font-bold leading-7 text-error">
              Authentication failed
            </Text>
            <Text className="text-base leading-6 text-center text-foreground">
              {errorMessage}
            </Text>
          </>
        )}
      </ThemedView>
    </SafeAreaView>
  );
}
