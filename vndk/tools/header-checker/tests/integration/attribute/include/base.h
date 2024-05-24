#define __INTRODUCED_IN(api_level) \
  __attribute__((__availability__(android, introduced = api_level)))

struct Struct {
  int ignored_field __INTRODUCED_IN(36);
  int field __attribute__((availability(macos, unavailable)));
} __INTRODUCED_IN(35);

struct IgnoredStruct {
  int field;
} __INTRODUCED_IN(36);

enum {
  ALPHABETICALLY_SMALLEST_IGNORED_FIELD __INTRODUCED_IN(36),
  DEPRECATED __attribute__((__availability__(android, deprecated = 35))),
  FIELD,
  OBSOLETED __attribute__((__availability__(android, obsoleted = 35))),
  UNAVAILABLE __attribute__((__availability__(android, unavailable))),
} __INTRODUCED_IN(35);

extern "C" {
int func(Struct*, IgnoredStruct*) __INTRODUCED_IN(35);
int ignored_func() __INTRODUCED_IN(36);
int var __INTRODUCED_IN(35);
int ignored_var __INTRODUCED_IN(36);
}
