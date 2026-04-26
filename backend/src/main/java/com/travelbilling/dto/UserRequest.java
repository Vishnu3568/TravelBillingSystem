package com.travelbilling.dto;

import lombok.Data;

@Data
public class UserRequest {
    private String username;
    private String password;
    private String fullName;
    private String email;
    private String role;
    private Boolean active;
}
