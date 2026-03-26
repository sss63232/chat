package com.example.chatgpt.controller;

import com.example.chatgpt.dto.CreateSessionRequest;
import com.example.chatgpt.model.ChatMessage;
import com.example.chatgpt.model.ChatSession;
import com.example.chatgpt.service.ChatSessionService;
import jakarta.validation.Valid;
import lombok.RequiredArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequiredArgsConstructor
@RequestMapping("/api/sessions")
public class SessionController {
    private final ChatSessionService chatSessionService;

    @PostMapping
    public ChatSession createSession(@Valid @RequestBody CreateSessionRequest request) {
        return chatSessionService.createSession(request.getUserId(), request.getTitle());
    }

    @GetMapping
    public List<ChatSession> getSessions(@RequestParam String userId) {
        return chatSessionService.getSessionsByUser(userId);
    }

    @GetMapping("/{id}/messages")
    public List<ChatMessage> getMessages(@PathVariable String id) {
        return chatSessionService.getMessagesBySession(id);
    }
}
