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
  assigns         s->size;
  ensures  valid: \valid(s) && StackInvariant(s);
  behavior empty:
    assumes            StackEmpty(s);
    assigns            \nothing;
    ensures empty:     StackEmpty(s);
    ensures unchanged: StackUnchanged{Old,Here}(s);
  behavior not_empty:
    assumes            !StackEmpty(s);
    assigns            s->size;
    ensures size:      StackSize(s) == StackSize{Old}(s) - 1;
    ensures full:      !StackFull(s);
    ensures storage:   StackStorage(s) == StackStorage{Old}(s);
    ensures capacity:  StackCapacity(s) == StackCapacity{Old}(s);
    ensures unchanged: Unchanged{Old,Here}(StackStorage(s), StackSize(s));
  complete behaviors;
  disjoint behaviors;
*/
void
stack_pop(Stack* s);
/*@
  requires valid:      \valid(s) && StackInvariant(s);
  assigns              s->size, s->obj[s->size];
  behavior full:
    assumes            StackFull(s);
    assigns            \nothing;
    ensures valid:     \valid(s) && StackInvariant(s);
    ensures full:      StackFull(s);
    ensures unchanged: StackUnchanged{Old,Here}(s);
  behavior not_full:
    assumes            !StackFull(s);
    assigns            s->size;
    assigns            s->obj[s->size];
    ensures valid:     \valid(s) && StackInvariant(s);
    ensures size:      StackSize(s) == StackSize{Old}(s) + 1;
    ensures top:       StackTop(s) == v;
    ensures storage:   StackStorage(s) == StackStorage{Old}(s);
    ensures capacity:  StackCapacity(s) == StackCapacity{Old}(s);
    ensures not_empty: !StackEmpty(s);
    ensures unchanged: Unchanged{Old,Here}(StackStorage(s), StackSize{Old}(s));
  complete behaviors;
  disjoint behaviors;
*/
void
stack_push(Stack* s, value_type v);
void
axiom_pop_of_push(Stack* s, value_type v)
{
  stack_push(s, v);
  stack_pop(s);
  //@ assert StackEqual{Pre,Here}(s, s);
}