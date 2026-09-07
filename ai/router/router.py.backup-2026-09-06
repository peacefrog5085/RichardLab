import time

from .health import ProviderHealth


class AIRouter:

    def __init__(self, config, provider_factory):
        self.config = config
        self.provider_factory = provider_factory

    def health(self):
        results = {}

        providers = self.config.get(
            "providers",
            {}
        )

        for name in providers:
            try:
                provider = self.provider_factory(
                    name,
                    self.config
                )

                raw = provider.health()

                status = raw.get(
                    "status",
                    "UNKNOWN"
                )

                if status == "READY":
                    reason = None
                else:
                    reason = raw.get(
                        "reason"
                    ) or raw.get(
                        "error"
                    )

                results[name] = ProviderHealth(
                    provider=name,
                    status=status,
                    reason=reason,
                    model=raw.get("model"),
                    latency_seconds=raw.get(
                        "elapsed_seconds"
                    ),
                    metadata=raw
                )

            except Exception as exc:
                results[name] = ProviderHealth(
                    provider=name,
                    status="ERROR",
                    reason=str(exc)
                )

        return results

    def choose(self):
        routing = self.config.get(
            "routing",
            {}
        )

        primary = routing.get(
            "primary"
        )

        if not primary:
            raise RuntimeError(
                "No AI primary provider configured."
            )

        health = self.health()

        primary_health = health.get(primary)

        if primary_health and primary_health.usable:
            provider = self.provider_factory(
                primary,
                self.config
            )
            return provider, health

        fallback = routing.get(
            "fallback"
        )

        if fallback:
            fallback_health = health.get(
                fallback
            )

            if fallback_health and fallback_health.usable:
                provider = self.provider_factory(
                    fallback,
                    self.config
                )
                return provider, health

        return None, health

    def ask(self, prompt, system=None):
        provider, health = self.choose()

        if provider is None:
            states = {
                name: item.as_dict()
                for name, item in health.items()
            }

            raise RuntimeError(
                "No usable AI provider available. "
                f"Provider states: {states}"
            )

        start = time.time()

        result = provider.ask(
            prompt,
            system=system
        )

        elapsed = time.time() - start

        if result.metadata is None:
            result.metadata = {}

        result.metadata["router_elapsed_seconds"] = (
            elapsed
        )

        return result, health
