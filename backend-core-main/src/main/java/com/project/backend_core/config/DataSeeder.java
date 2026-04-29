package com.project.backend_core.config;

import com.project.backend_core.entity.User;
import com.project.backend_core.entity.enums.UserRole;
import com.project.backend_core.repository.UserRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.boot.CommandLineRunner;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Component;

@Component
@RequiredArgsConstructor
public class DataSeeder implements CommandLineRunner {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;

    @Override
    public void run(String... args) {
        if (userRepository.findByEmail("admin@system.com").isEmpty()) {
            var admin = User.builder()
                    .firstname("System")
                    .lastname("Admin")
                    .email("admin@system.com")
                    .password(passwordEncoder.encode("Admin@123"))
                    .role(UserRole.ADMIN)
                    .build();
            userRepository.save(admin);
            System.out.println("Default admin seeded: admin@system.com / Admin@123");
        }
    }
}