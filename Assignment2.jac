

with entry {
    spawn file_agent;
    do file_agent.read_code("uploads/sample.php");
}

# Agent to read file
behavior file_agent {
    can read_code(path) {
        log("📂 Reading file: " + path);
        file_text = read(path);
        if not file_text {
            log("⚠️ Error: Could not read file at " + path);
            return;
        }
        spawn parser_agent with file_text;
    }
}

# Agent to parse functions from file
behavior parser_agent {
    has file_text;

    can parse_code() {
        log("🧩 Parsing PHP code...");
        lines = split_lines(file_text);
        functions = [];

        foreach line in lines {
            if contains(line, "function") {
                log("✅ Function found: " + line);
                append(functions, line);
            }
        }

        if len(functions) > 0 {
            spawn doc_agent with functions;
        } else {
            log("⚠️ No functions found in the file.");
        }
    }

    on spawn {
        do parse_code();
    }
}

# Agent to generate documentation
behavior doc_agent {
    has functions;

    can generate_docs() {
        log("📝 Generating documentation...");
        foreach func in functions {
            log("📖 Documented function: " + func);
        }
        log("✅ Documentation generation complete!");
    }

    on spawn {
        do generate_docs();
    }
}
