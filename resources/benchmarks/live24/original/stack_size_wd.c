#include <limits.h>
#ifndef __cplusplus
typedef int bool;
#define false		((bool)0)
#define true		((bool)1)
#endif
typedef int value_type;
#define VALUE_TYPE_MAX  INT_MAX
#define VALUE_TYPE_MIN  INT_MIN
typedef unsigned int size_type;
#define SIZE_TYPE_MAX  UINT_MAX
struct Stack
{
  value_type* obj;
  size_type   capacity;
  size_type   size;
};
typedef struct Stack Stack;
/*@
  axiomatic Unchanged
  {
    predicate
    Unchanged{K,L}(value_type* a, integer m, integer n) =
      \forall integer i; m <= i < n ==>  \at(a[i],K) == \at(a[i],L);
    predicate
    Unchanged{K,L}(value_type* a, integer n) = Unchanged{K,L}(a, 0, n);
  }
*/
/*@
  axiomatic Equal
  {
    predicate
    Equal{K,L}(value_type* a, integer m, integer n, value_type* b) =
      \forall integer i; m <= i < n  ==>  \at(a[i],K) == \at(b[i],L);
    predicate
    Equal{K,L}(value_type* a, integer n, value_type* b) =
      Equal{K,L}(a, 0, n, b);
    predicate
    Equal{K,L}(value_type* a, integer m, integer n,
               value_type* b, integer p) = Equal{K,L}(a+m, n-m, b+p);
    predicate
    Equal{K,L}(value_type* a, integer m, integer n, integer p) =
      Equal{K,L}(a, m, n, a, p);
  }
*/
/*@
  axiomatic StackInvariant
  {
    logic integer
    StackCapacity{L}(Stack* s) = s->capacity;
    logic integer
    StackSize{L}(Stack* s) = s->size;
    logic value_type*
    StackStorage{L}(Stack* s) = s->obj;
    logic integer
    StackTop{L}(Stack* s) = s->obj[s->size-1];
    predicate
    StackEmpty{L}(Stack* s) =  StackSize(s) == 0;
    predicate
    StackFull{L}(Stack* s)  =  StackSize(s) == StackCapacity(s);
    predicate
    StackInvariant{L}(Stack* s) =
      0 < StackCapacity(s) &&
      0 <= StackSize(s) <= StackCapacity(s) &&
      \valid(StackStorage(s) + (0..StackCapacity(s)-1)) &&
      \separated(s, StackStorage(s) + (0..StackCapacity(s)-1));
  }
*/
/*@
  axiomatic StackUtility
  {
    predicate
    StackSeparated(Stack* s, Stack* t) =
      \separated(s, s->obj + (0..s->capacity-1),
                 t, t->obj + (0..t->capacity-1));
    predicate
    StackUnchanged{K,L}(Stack* s) =
      StackSize{K}(s)     == StackSize{L}(s)      &&
      StackStorage{K}(s)  == StackStorage{L}(s)   &&
      StackCapacity{K}(s) == StackCapacity{L}(s)  &&
      Unchanged{K,L}(StackStorage{K}(s), StackSize{K}(s));
  }
*/
/*@
  axiomatic StackEquality
  {
    predicate
    StackEqual{S,T}(Stack* s, Stack* t) =
      StackSize{S}(s) == StackSize{T}(t) &&
      Equal{S,T}(StackStorage{S}(s), StackSize{S}(s), StackStorage{T}(t));
    lemma StackEqual_Reflexive{S} :
      \forall Stack* s; StackEqual{S,S}(s, s);
    lemma StackEqual_Symmetric{S,T} :
      \forall Stack *s, *t;
        StackEqual{S,T}(s, t)  ==>  StackEqual{T,S}(t, s);
    lemma StackEqual_Transitive{S,T,U}:
      \forall Stack *s, *t, *u;
        StackEqual{S,T}(s, t)  ==>
        StackEqual{T,U}(t, u)  ==>
        StackEqual{S,U}(s, u);
  }
*/
/*@
    requires valid: \valid(s) && StackInvariant(s);
    assigns         \nothing;
    ensures  size:  \result == StackSize(s);
*/
size_type
stack_size(const Stack* s);
bool
stack_size_wd(const Stack* s, const Stack* t)
{
  return stack_size(s) == stack_size(t);
}
int main(){
  value_type a[5] = {1, 2, 3, 4, 5};
  value_type b[5] = {1, 2, 3, 4, 5};
  Stack s1, s2;
  s1.capacity = 5;
  s1.size = 5;
  s1.obj = a;
  s2.capacity = 5;
  s2.size = 5;
  s2.obj = b;
  bool result = stack_size_wd(&s1, &s2);
  //@ assert result == true;
}