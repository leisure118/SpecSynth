int max3(int a,int b,int c) {
      int max;
      if((a >= b) && (a >= c)) {
        max = a;
      }
      else if((b >= a) && (b >= c)) {
        max = b;
      }
      else if((c >= a) && (c >= b)) {
        max = c;
      }
    return max;
}
int main(){
    int a = 10;
    int b = 20;
    int c = 30;
    int max = max3(a,b,c);
    //@ assert max == 30;
}