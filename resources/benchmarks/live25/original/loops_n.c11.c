#include <limits.h>
/*@
assigns \nothing;
ensures INT_MIN <= \result < INT_MAX;
*/
int unknown();
int main(){
   int a[5];
   unsigned int len=0;
   int i;
   while(unknown()){
      if (len==4)
         len =0;
      a[len]=0;
      len++;
   }
   //@ assert(len>=0 && len<5);
   return 1;
}
