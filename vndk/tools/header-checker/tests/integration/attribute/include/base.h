#define ANNOTATE(V) __attribute__((annotate("introduced_in_llndk=" #V)))

struct Struct {
  int field __attribute__((annotate("unknown", 1)));
  int ignored ANNOTATE(202504);
} ANNOTATE(202404);

struct IgnoredStruct {
  int ignored;
} ANNOTATE(202504);

enum Enum { IGNORED_1 ANNOTATE(202504), FIELD } ANNOTATE(202404);

enum IgnoredEnum { IGNORED_2 } ANNOTATE(202504);

extern "C" {
int func(Struct*, Enum) ANNOTATE(202404);
int ignored_func(IgnoredStruct*, IgnoredEnum*) ANNOTATE(202504);
int var ANNOTATE(202404);
int ignored_var ANNOTATE(202504);
}
