package com.example.chatgpt.service;

import com.example.chatgpt.dto.SendMessageResponse;
import com.example.chatgpt.model.ChatMessage;
import com.example.chatgpt.model.MessageRole;
import com.example.chatgpt.repository.ChatMessageRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.time.Instant;
import java.util.ArrayList;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ChatService {
    private final ChatMessageRepository chatMessageRepository;
    private final ChatSessionService chatSessionService;
    private final MinioService minioService;

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

        String assistantContent = mockAssistantReply(content);
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

    private String mockAssistantReply(String content) {
        return "[Mock AI Reply] 我已收到你的訊息：" + content;
    }
}
