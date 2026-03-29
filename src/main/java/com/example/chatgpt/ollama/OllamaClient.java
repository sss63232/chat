package com.example.chatgpt.ollama;

import com.example.chatgpt.config.OllamaProperties;
import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.RequiredArgsConstructor;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestClient;

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.function.Consumer;

@Service
@RequiredArgsConstructor
public class OllamaClient {
    private final RestClient ollamaRestClient;
    private final OllamaProperties properties;
    private final ObjectMapper objectMapper;

    public String chat(List<OllamaMessage> messages) {
        OllamaChatRequest request = new OllamaChatRequest(
                properties.getModel(),
                messages,
                false,
                null
        );

        OllamaChatResponse response = ollamaRestClient.post()
                .uri("/api/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .retrieve()
                .body(OllamaChatResponse.class);

        if (response == null || response.message() == null || response.message().content() == null) {
            throw new IllegalStateException("Ollama returned an empty response");
        }

        return response.message().content();
    }

    public String chatStream(List<OllamaMessage> messages, Consumer<String> onDelta) {
        OllamaChatRequest request = new OllamaChatRequest(
                properties.getModel(),
                messages,
                true,
                null
        );

        StringBuilder fullResponse = new StringBuilder();

        ollamaRestClient.post()
                .uri("/api/chat")
                .contentType(MediaType.APPLICATION_JSON)
                .body(request)
                .exchange((clientRequest, clientResponse) -> {
                    try (BufferedReader reader = new BufferedReader(
                            new InputStreamReader(clientResponse.getBody(), StandardCharsets.UTF_8))) {
                        String line;
                        while ((line = reader.readLine()) != null) {
                            if (line.isBlank()) {
                                continue;
                            }
                            OllamaStreamResponse chunk = objectMapper.readValue(line, OllamaStreamResponse.class);
                            if (chunk.message() != null && chunk.message().content() != null) {
                                String delta = chunk.message().content();
                                if (!delta.isEmpty()) {
                                    fullResponse.append(delta);
                                    if (onDelta != null) {
                                        onDelta.accept(delta);
                                    }
                                }
                            }
                            if (Boolean.TRUE.equals(chunk.done())) {
                                break;
                            }
                        }
                    }
                    return null;
                });

        if (fullResponse.isEmpty()) {
            throw new IllegalStateException("Ollama returned an empty response");
        }

        return fullResponse.toString();
    }
}
