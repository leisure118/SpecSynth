#include<limits.h>
/*@
  requires val != -2147483648;
  assigns \nothing;
  ensures \result == (val < 0 ? -val : val);
  ensures \result >= 0;
*/
int abs(int val){
if(val<0)
return -val;
else
return val;
}
/*@
  assigns \nothing;
  ensures \result == 0;
*/
int main(){
int x=4;
int r=abs(x);
//@assert x==4;
}
