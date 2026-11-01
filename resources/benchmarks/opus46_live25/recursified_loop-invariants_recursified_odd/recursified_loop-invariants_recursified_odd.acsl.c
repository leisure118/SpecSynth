#include<limits.h>
/*@ lemma cast_uint_no_overflow: \forall integer x; 0 <= x <= 4294967293 ==> (unsigned int)(2 + x) == 2 + x; */
/*@ lemma cast_uint_wrap: (unsigned int)(4294967297) == 1; */
/*@ lemma add2_odd: \forall integer x; x % 2 == 1 ==> (2 + x) % 2 == 1; */
/*@ lemma parity_uint_add2_safe: \forall integer x; 0 <= x <= 4294967293 ==> x % 2 == 1 ==> (unsigned int)(2 + x) % 2 == 1; */
/*@ lemma parity_uint_max: (unsigned int)(2 + 4294967295) % 2 == 1; */
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
/*@
  requires \valid(x);
  requires *x % 2 == 1;
  assigns *x;
  ensures *x % 2 == 1;
*/
void func_to_recursive_line_13_to_14_0(unsigned int *x)
{
  if (unknown())
  {
    {
      *x += 2;
    }
    //@ assert \at(*x, Pre) <= 4294967293 ==> *x % 2 == 1;
    //@ assert \at(*x, Pre) == 4294967295 ==> *x % 2 == 1;
    //@ assert *x % 2 == 1;
    func_to_recursive_line_13_to_14_0(x);
  }
  else
  {
  }
}
int main(void)
{
  unsigned int x = 1;
  func_to_recursive_line_13_to_14_0(&x);
  //@ assert(x % 2);
  return 0;
}
