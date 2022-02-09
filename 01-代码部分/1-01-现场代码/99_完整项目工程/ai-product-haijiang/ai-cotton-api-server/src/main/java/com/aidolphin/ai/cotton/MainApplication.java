package com.aidolphin.ai.cotton;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;
import org.springframework.boot.web.servlet.ServletComponentScan;
import org.springframework.cache.annotation.EnableCaching;
import org.springframework.scheduling.annotation.EnableScheduling;

//禁掉springboot的自动注入
@SpringBootApplication(exclude = { DataSourceAutoConfiguration.class })
//开启redis缓存
@EnableCaching
@EnableScheduling
//该注解会扫描相应的包
@ServletComponentScan
@MapperScan("com.aidolphin.ai.cotton.mapper")
public class MainApplication {

    public static void main(String[] args) {
        SpringApplication.run(MainApplication.class, args);
    }

}
