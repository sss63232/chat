package com.example.chatgpt.ollama;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

import java.util.List;
import java.util.Map;

@JsonIgnoreProperties(ignoreUnknown = true)
public record OllamaChatRequest(
        String model,
        List<OllamaMessage> messages,
        boolean stream,
        Map<String, Object> options
) {
}
