#include<limits.h>
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