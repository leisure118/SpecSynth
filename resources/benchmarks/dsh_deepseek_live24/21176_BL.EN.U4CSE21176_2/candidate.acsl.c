#include<limits.h>
/*@
  requires -100 <= a <= 100;
  requires -100 <= b <= 100;
  assigns \nothing;
  ensures \result == (a >= 0 ? a + 1 : a + b);
*/
int foo(int a,int b){
if(a>=0){
a++;
}
else{
a+=b;
}
return a;
}
int main(){
int x=-99;
int y=100;
int r=foo(x,y);
//@assert x==-99 && y==100 && r==1;
}