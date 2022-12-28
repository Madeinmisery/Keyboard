struct Struct {
  int array[];
};

extern "C" {
void StructMember(Struct &);
void Pointer(int *);
void Pointer2(int (*)[10]);
void Reference(int (&)[][11]);
void Element(short (*)[2]);
}
