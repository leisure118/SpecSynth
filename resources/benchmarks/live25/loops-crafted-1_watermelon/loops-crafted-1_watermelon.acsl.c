#include<limits.h>
/*@
assigns \nothing;
ensures 0 < \result < 10000000;
*/
int unknown();
int true = 1;
int false = 0;

int main(){
  int w=unknown();
  int is_divisible1 = true, is_divisible2 = true;
  if(w > 0 && w < 10000000)
  {
    // correct_version(w) inlined
    {
      int wv = w;
      int is_div = true;
      if(wv < 4) {
        is_div = false;
      } else {
        int i;
        /*@
          loop invariant 0 <= i;
          loop invariant i % 2 == 0;
          loop invariant wv > 0 ==> i <= wv+1;
          loop assigns i;
          loop variant wv - i;
        */
        for(i = 0; i < wv; i += 2) {}
        if(i != wv)
          is_div = false;
      }
      is_divisible1 = is_div;
    }
    // student_version(w) inlined
    {
      int wv = w;
      int is_div = true;
      if(wv < 4) {
        is_div = false;
      } else {
        int i;
        /*@
          loop invariant 0 <= i;
          loop invariant i % 2 == 0;
          loop invariant wv > 0 ==> i <= wv+1;
          loop assigns i;
          loop variant wv - i;
        */
        for(i = 0; i < wv; i += 2) {}
        if(i != wv)
          is_div = false;
      }
      is_divisible2 = is_div;
    }
    //@ assert(is_divisible1 == is_divisible2);
  }
  return 0;
}
