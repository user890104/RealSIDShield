#ifndef LATCH_H
#define LATCH_H

class Latch
{
  void Latch::Enable(void);
  void Latch::Disable(void);

  public:
    void Setup();
    void SetAddress(uint8_t address, uint8_t read);
};

#endif //LATCH_H
