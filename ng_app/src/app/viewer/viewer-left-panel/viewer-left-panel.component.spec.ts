import { ComponentFixture, TestBed } from '@angular/core/testing';

import { ViewerLeftPanelComponent } from './viewer-left-panel.component';

describe('SessionSelectorComponent', () => {
  let component: ViewerLeftPanelComponent;
  let fixture: ComponentFixture<ViewerLeftPanelComponent>;

  beforeEach(async () => {
    await TestBed.configureTestingModule({
      imports: [ViewerLeftPanelComponent]
    })
    .compileComponents();

    fixture = TestBed.createComponent(ViewerLeftPanelComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
