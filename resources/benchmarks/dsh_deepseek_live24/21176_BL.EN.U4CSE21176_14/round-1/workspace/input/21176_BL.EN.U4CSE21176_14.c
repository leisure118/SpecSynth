#include<limits.h>
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