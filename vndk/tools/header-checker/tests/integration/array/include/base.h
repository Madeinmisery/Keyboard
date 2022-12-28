struct Struct {
  int array[0];
};

extern "C" {
void StructMember(Struct &);
void Pointer(int[]);
void Pointer2(int (*)[]);
void Reference(int (&)[][1]);
void Element(int (*)[2]);
}
