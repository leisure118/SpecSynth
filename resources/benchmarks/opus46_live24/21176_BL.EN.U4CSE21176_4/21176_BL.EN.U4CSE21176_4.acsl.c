#include<limits.h>
/*@
  requires n == n;
  assigns \nothing;
  ensures (n % 2 == 0) ==> \result == 1;
  ensures (n % 2 != 0) ==> \result == 0;
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
