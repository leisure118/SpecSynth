int found;
/*@ 
requires \valid(t+(0..4));
*/
void f(int*t, int x) {
  int i = 0;
  found = 0;
 first_loop:
  /*@
    loop invariant 0 <= i <= 5;
    loop invariant found <==> \exists integer j; 0 <= j < i && t[j] == x;
    loop assigns i, found;
    loop variant 5 - i;
  */
  for(; i <= 4; i++) {
    if(t[i] == x)
      found = 1;
  }
  //@ assert found <==> \exists integer i; 0 <= i <= 4 && t[i] == x;
}