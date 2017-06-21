package org.appnexus.engsupportAPI;

import org.springframework.hateoas.ResourceSupport;

import com.fasterxml.jackson.annotation.JsonCreator;
import com.fasterxml.jackson.annotation.JsonProperty;
import com.google.gson.Gson;
import com.google.gson.JsonObject;

public class JSONText extends ResourceSupport {

    private JsonObject content;

    @JsonCreator
    public JSONText(@JsonProperty("content") String content) {
		this.content = new Gson().fromJson(content, JsonObject.class);
    }

    public JsonObject getContent() {
        return content;
    }
}
