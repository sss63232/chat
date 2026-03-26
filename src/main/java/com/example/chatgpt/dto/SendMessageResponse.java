package com.example.chatgpt.dto;

import lombok.Builder;
import lombok.Data;

import java.util.List;

@Data
@Builder
public class SendMessageResponse {
    private String sessionId;
    private String userMessageId;
    private String assistantMessageId;
    private String assistantContent;
    private List<String> attachmentUrls;
}
