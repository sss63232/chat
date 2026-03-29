package com.example.chatgpt.service;

import com.example.chatgpt.dto.SendMessageResponse;
import com.example.chatgpt.model.ChatMessage;
import com.example.chatgpt.model.MessageRole;
import com.example.chatgpt.ollama.OllamaClient;
import com.example.chatgpt.ollama.OllamaMessage;
import com.example.chatgpt.repository.ChatMessageRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletableFuture;

@Service
@RequiredArgsConstructor
public class ChatService {
    private final ChatMessageRepository chatMessageRepository;
    private final ChatSessionService chatSessionService;
    private final MinioService minioService;
    private final OllamaClient ollamaClient;

    public SendMessageResponse sendMessage(String sessionId, String content, MultipartFile file) {
        chatSessionService.getSessionOrThrow(sessionId);

        List<String> attachmentUrls = new ArrayList<>();
        if (file != null && !file.isEmpty()) {
            String objectName = minioService.uploadFile(file);
            attachmentUrls.add(objectName);
        }

        ChatMessage userMessage = ChatMessage.builder()
                .sessionId(sessionId)
                .role(MessageRole.USER)
                .content(content)
                .attachmentUrls(attachmentUrls)
                .createdAt(Instant.now())
                .build();
        userMessage = chatMessageRepository.save(userMessage);

        List<OllamaMessage> history = chatSessionService.getMessagesBySession(sessionId).stream()
                .map(this::toOllamaMessage)
                .toList();
        String assistantContent = ollamaClient.chat(history);
        ChatMessage assistantMessage = ChatMessage.builder()
                .sessionId(sessionId)
                .role(MessageRole.ASSISTANT)
                .content(assistantContent)
                .attachmentUrls(List.of())
                .createdAt(Instant.now())
                .build();
        assistantMessage = chatMessageRepository.save(assistantMessage);

        return SendMessageResponse.builder()
                .sessionId(sessionId)
                .userMessageId(userMessage.getId())
                .assistantMessageId(assistantMessage.getId())
                .assistantContent(assistantContent)
                .attachmentUrls(attachmentUrls)
                .build();
    }

    public SseEmitter streamMessage(String sessionId, String content, MultipartFile file) {
        chatSessionService.getSessionOrThrow(sessionId);

        List<String> attachmentUrls = new ArrayList<>();
        if (file != null && !file.isEmpty()) {
            String objectName = minioService.uploadFile(file);
            attachmentUrls.add(objectName);
        }

        ChatMessage userMessage = ChatMessage.builder()
                .sessionId(sessionId)
                .role(MessageRole.USER)
                .content(content)
                .attachmentUrls(attachmentUrls)
                .createdAt(Instant.now())
                .build();
        userMessage = chatMessageRepository.save(userMessage);

        SseEmitter emitter = new SseEmitter(0L);
        ChatMessage savedUserMessage = userMessage;

        CompletableFuture.runAsync(() -> {
            try {
                List<OllamaMessage> history = chatSessionService.getMessagesBySession(sessionId).stream()
                        .map(this::toOllamaMessage)
                        .toList();

                String assistantContent = ollamaClient.chatStream(history, delta -> {
                    try {
                        emitter.send(SseEmitter.event().name("delta").data(delta));
                    } catch (Exception ex) {
                        throw new IllegalStateException("Failed to send stream chunk", ex);
                    }
                });

                ChatMessage assistantMessage = ChatMessage.builder()
                        .sessionId(sessionId)
                        .role(MessageRole.ASSISTANT)
                        .content(assistantContent)
                        .attachmentUrls(List.of())
                        .createdAt(Instant.now())
                        .build();
                assistantMessage = chatMessageRepository.save(assistantMessage);

                SendMessageResponse response = SendMessageResponse.builder()
                        .sessionId(sessionId)
                        .userMessageId(savedUserMessage.getId())
                        .assistantMessageId(assistantMessage.getId())
                        .assistantContent(assistantContent)
                        .attachmentUrls(attachmentUrls)
                        .build();

                emitter.send(SseEmitter.event().name("done").data(response));
                emitter.complete();
            } catch (Exception e) {
                emitter.completeWithError(e);
            }
        });

        return emitter;
    }

    private OllamaMessage toOllamaMessage(ChatMessage message) {
        String combinedContent = message.getContent() == null ? "" : message.getContent();
        if (message.getAttachmentUrls() != null && !message.getAttachmentUrls().isEmpty()) {
            StringBuilder builder = new StringBuilder();
            builder.append(combinedContent);
            builder.append("\n\nAttachments:\n");
            for (String attachmentUrl : message.getAttachmentUrls()) {
                builder.append("- ").append(attachmentUrl).append('\n');
            }
            combinedContent = builder.toString().trim();
        }
        return new OllamaMessage(message.getRole().getValue(), combinedContent);
    }
}
