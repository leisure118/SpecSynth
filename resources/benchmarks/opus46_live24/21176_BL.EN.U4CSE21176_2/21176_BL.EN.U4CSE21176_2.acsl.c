#include<limits.h>
/*@
  assigns \nothing;
  ensures \old(a) >= 0 ==> \result == \old(a) + 1;
  ensures \old(a) < 0 ==> \result == \old(a) + \old(b);
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