node file {
    has path: str;
    has content: str;
}

node doc {
    has title: str;
    has body: str;
    has lang: str;
}

edge for_file {}

node file {
    can extract {
        std.out("extract ability invoked for: " + here.path);
    }
}

walker docger {
    has files_seen: int = 0;

    root {
        std.out("docger walker starting");
        take -->;
    }

    file {
        std.out("docger visiting: " + here.path);
        files_seen = files_seen + 1;
        here.extract();
    }

    end {
        std.out("docger finished. files_seen: " + files_seen);
    }
}
