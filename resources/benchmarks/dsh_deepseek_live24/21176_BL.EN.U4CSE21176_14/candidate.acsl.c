#include<limits.h>
/*@
  requires val != -2147483648;
  assigns \nothing;
  ensures \result == (val > 0 ? val : (val < 0 ? -val : 0));
*/
int check(int val){
if(val>0)
return val;
else if(val<0)
return -val;
else
return 0;
}
int main(){
int x=4;
int r=check(x);
//@assert x==4;
}