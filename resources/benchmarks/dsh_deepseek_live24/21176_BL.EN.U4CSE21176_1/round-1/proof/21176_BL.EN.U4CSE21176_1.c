#include<limits.h>
/*@
  requires \true;
  assigns \nothing;
  ensures \result == (a > b ? a : b);
  ensures \result >= a && \result >= b;
*/
int max(int a,int b){
return a>b?a:b;
}
int main(){
int x=4;
int y=5;
int r=max(x,y);
//@assert x==4 && y==5;
}
