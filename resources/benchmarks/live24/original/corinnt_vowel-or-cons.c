enum Kind { VOWEL, CONSONANT };
enum Kind kind_of_letter(char c) {
    if (c == 'a' || c == 'e' || c == 'i' || c == 'o' || c == 'u'){
        return VOWEL; 
    }
    return CONSONANT;
}
void test(){
    char a = 'a', b = 'b', c = 'c', e = 'e', z = 'z'; 
    enum Kind kind_a = kind_of_letter(a); 
    //@ assert kind_a == VOWEL ;
    enum Kind kind_b = kind_of_letter(b); 
    //@ assert kind_b == CONSONANT ;
    enum Kind kind_c = kind_of_letter(c); 
    //@ assert kind_c == CONSONANT ;
    enum Kind kind_e = kind_of_letter(e); 
    //@ assert kind_e == VOWEL ;
    enum Kind kind_z = kind_of_letter(z); 
    //@ assert kind_z == CONSONANT ;
}