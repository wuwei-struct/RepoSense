package demo;

import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
public class ApiController {
    @GetMapping("/users/{id}")
    public String getUser() {
        return "ok";
    }

    @PostMapping("/orders")
    public String createOrder() {
        return "ok";
    }
}
