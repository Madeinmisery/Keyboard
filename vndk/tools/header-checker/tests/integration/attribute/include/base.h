#define ANNOTATE(V) __attribute__((annotate("introduced_in_llndk=" #V)))

struct Struct {
  int field __attribute__((annotate("unknown", 1)));
  int ignored ANNOTATE(202504);
} ANNOTATE(202404);

struct Ignored {
  int ignored;
} ANNOTATE(202504);

enum Enum { IGNORED ANNOTATE(202504), FIELD } ANNOTATE(202404);

extern "C" {
int func(Struct*, Ignored*, Enum) ANNOTATE(202404);
int ignored_func() ANNOTATE(202504);
int var ANNOTATE(202404);
int ignored_var ANNOTATE(202504);
}
