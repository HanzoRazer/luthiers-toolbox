# Add this method to the LLMClient class

    # Image Generation (OpenAI Image API transport)
    # -----------------------------------------------------------------------

    def generate_image_bytes(
        self,
        *,
        prompt: str,
        size: str = "1024x1024",
        format: str = "png",
        model: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> tuple[bytes, Dict[str, Any]]:
        """
        Generate an image via OpenAI Image API: POST /v1/images/generations

        Returns:
            (image_bytes, meta_dict)

        Notes:
        - GPT image models (gpt-image-1, etc.) return base64-encoded images. :contentReference[oaicite:2]{index=2}
        - We decode the first returned image and return raw bytes.
        """
        prompt = (prompt or "").strip()
        if not prompt:
            raise LLMClientError("generate_image_bytes requires a non-empty prompt")

        if self.config.provider != LLMProvider.OPENAI:
            raise LLMClientError(
                f"generate_image_bytes currently supports provider=openai only (got {self.config.provider})"
            )

        if not self.config.api_key:
            raise LLMAuthError("Missing OPENAI_API_KEY (set env var or pass in LLMConfig.api_key)")

        # Safe default for image generation
        used_model = model or "gpt-image-1"

        options = options or {}

        # Per OpenAI Images API request body :contentReference[oaicite:3]{index=3}
        body: Dict[str, Any] = {
            "model": used_model,
            "prompt": prompt,
            "n": int(options.get("n", 1)),
            "size": size,
        }

        # GPT Image models use output_format/output_compression (not response_format). :contentReference[oaicite:4]{index=4}
        # Keep request conservative; only send fields when present.
        if format:
            body["output_format"] = format
        if "quality" in options:
            body["quality"] = options["quality"]
        if "background" in options:
            body["background"] = options["background"]
        if "moderation" in options:
            body["moderation"] = options["moderation"]
        if "output_compression" in options:
            body["output_compression"] = options["output_compression"]
        if "user" in options:
            body["user"] = options["user"]

        url = (self.config.base_url or "https://api.openai.com/v1").rstrip("/") + "/images/generations"

        last_err: Optional[Exception] = None
        for attempt in range(1, self.config.max_retries + 1):
            try:
                sess = self._get_session()
                resp = sess.post(url, headers=self._get_headers(), json=body)

                # Auth
                if resp.status_code in (401, 403):
                    raise LLMAuthError(f"OpenAI auth failed (status={resp.status_code})")

                # Rate limit
                if resp.status_code == 429:
                    err = LLMRateLimitError("OpenAI rate limit exceeded (429)")
                    ra = resp.headers.get("retry-after")
                    try:
                        err.retry_after = float(ra) if ra else None
                    except Exception:
                        err.retry_after = None
                    raise err

                # Retry 5xx
                if 500 <= resp.status_code <= 599:
                    raise LLMClientError(f"OpenAI server error (status={resp.status_code})")

                if resp.status_code != 200:
                    # Best-effort surface message
                    try:
                        payload = resp.json()
                    except Exception:
                        payload = {"text": resp.text}
                    raise LLMResponseError(f"Unexpected status={resp.status_code} payload={payload}")

                payload = resp.json()
                data = payload.get("data") or []
                if not data or not isinstance(data, list):
                    raise LLMResponseError(f"Missing data[] in image response: {payload}")

                first = data[0] or {}

                # GPT image models always return base64-encoded images. :contentReference[oaicite:5]{index=5}
                b64 = first.get("b64_json")
                if not b64:
                    # Some models might return url when response_format=url, but GPT image models should be b64.
                    # Still, handle url defensively.
                    img_url = first.get("url")
                    if img_url:
                        # Fetch the image bytes (URL is time-limited).
                        img_resp = sess.get(img_url)
                        if img_resp.status_code != 200:
                            raise LLMResponseError(f"Failed to fetch image URL (status={img_resp.status_code})")
                        meta = {
                            "provider": "openai",
                            "model": payload.get("model", used_model),
                            "size": size,
                            "format": format,
                            "source": "url",
                        }
                        return (img_resp.content, meta)
                    raise LLMResponseError(f"No b64_json or url found in image response: {first}")

                try:
                    image_bytes = base64.b64decode(b64)
                except Exception as e:
                    raise LLMResponseError("Failed to decode base64 image payload") from e

                meta = {
                    "provider": "openai",
                    "model": payload.get("model", used_model),
                    "size": size,
                    "format": format,
                    "source": "b64_json",
                    "n": body.get("n", 1),
                }
                return (image_bytes, meta)

            except LLMRateLimitError as e:
                last_err = e
                # Prefer server-provided retry-after if present
                if getattr(e, "retry_after", None):
                    time.sleep(float(e.retry_after))
                else:
                    self._sleep_backoff(attempt)
            except LLMTimeoutError as e:
                last_err = e
                self._sleep_backoff(attempt)
            except LLMClientError as e:
                last_err = e
                if attempt >= self.config.max_retries:
                    break
                self._sleep_backoff(attempt)
            except Exception as e:
                # Unknown failure: retry a little, then fail
                last_err = e
                if attempt >= self.config.max_retries:
                    break
                self._sleep_backoff(attempt)

        raise LLMClientError(f"Image generation failed after {self.config.max_retries} attempts") from last_err
