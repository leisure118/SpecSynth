#include<limits.h>
/*@
  assigns \nothing;
  ensures \result >= 0;
  ensures val >= 0 ==> \result == val;
  ensures val < 0 ==> \result == -val;
*/
int abs(int val){
if(val<0)
return -val;
else
return val;
}
int main(){
int x=4;
int r=abs(x);
//@assert x==4;
}
