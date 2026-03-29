package com.example.chatgpt.ollama;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record OllamaStreamResponse(OllamaMessage message, Boolean done) {
}
