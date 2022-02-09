package com.aidolphin.ai.cotton.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.jdbc.DataSourceBuilder;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import javax.sql.DataSource;

@Configuration
public class DataSourceConfig {
	@Bean(name = "dataSourceCottonLocal")
	@ConfigurationProperties(prefix = "spring.datasource.dbcottonlocal") // application.properties中对应属性的前缀
	public DataSource dataSourceAiCottonLocal() {
		return DataSourceBuilder.create().build();
	}
}
