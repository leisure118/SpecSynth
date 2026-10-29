#include<limits.h>
/*@
  assigns \nothing;
  ensures \result == 1 || \result == 0;
  ensures \result == 1 <==> n % 2 == 0;
*/
int check(int n){
if(n%2==0)
return 1;
else
return 0;
}
int main(){
int a=4;
int r=check(a);
//@assert a==4;
}