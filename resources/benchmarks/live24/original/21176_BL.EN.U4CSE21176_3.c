#include<limits.h>
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