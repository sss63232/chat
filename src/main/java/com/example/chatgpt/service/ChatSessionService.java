package com.example.chatgpt.service;

import com.example.chatgpt.model.ChatMessage;
import com.example.chatgpt.model.ChatSession;
import com.example.chatgpt.repository.ChatMessageRepository;
import com.example.chatgpt.repository.ChatSessionRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.Instant;
import java.util.List;

@Service
@RequiredArgsConstructor
public class ChatSessionService {
    private final ChatSessionRepository chatSessionRepository;
    private final ChatMessageRepository chatMessageRepository;

    public ChatSession createSession(String userId, String title) {
        ChatSession session = ChatSession.builder()
                .userId(userId)
                .title(title)
                .createdAt(Instant.now())
                .build();
        return chatSessionRepository.save(session);
    }

    public List<ChatSession> getSessionsByUser(String userId) {
        return chatSessionRepository.findByUserIdOrderByCreatedAtDesc(userId);
    }

    public List<ChatMessage> getMessagesBySession(String sessionId) {
        return chatMessageRepository.findBySessionIdOrderByCreatedAtAsc(sessionId);
    }

    public ChatSession getSessionOrThrow(String sessionId) {
        return chatSessionRepository.findById(sessionId)
                .orElseThrow(() -> new IllegalArgumentException("Session not found: " + sessionId));
    }
}
